pragma solidity 0.5.12;

contract Vault9247 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        deposits[msg.sender] -= amount;
        reserve -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function totalDeposits() public view returns (uint256) { return reserve; }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }
}
