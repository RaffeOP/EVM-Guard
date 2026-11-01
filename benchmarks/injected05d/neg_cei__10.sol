pragma solidity 0.5.12;

contract Locker9309 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        total -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function ownerOf_() public view returns (address) { return owner; }

    function totalDeposits() public view returns (uint256) { return total; }
}
