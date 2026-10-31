pragma solidity 0.5.12;

contract Locker2563 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(credit[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        credit[msg.sender] -= amount;
        total -= amount;
        locked = false;
    }

    function totalDeposits() public view returns (uint256) { return total; }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }
}
