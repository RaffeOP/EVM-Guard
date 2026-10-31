pragma solidity 0.8.20;

contract Safe1061 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
